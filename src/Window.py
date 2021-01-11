import csv
from threading import Thread
import requests
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .Chart import PieChart
from .Crawler import AnalyzeCrawler, RedeemCrawler


class ProgressWindow(tk.Toplevel):
	def __init__(self, schedule):
		super().__init__(takefocus=True)
		self.title('下載中...')
		self.resizable(0, 0)
		self.done = schedule[0]
		self.total = schedule[1]
		self.prompt_text = tk.StringVar()
		self.progress_var = tk.DoubleVar()
		tk.Label(self, textvariable=self.prompt_text).pack()
		ttk.Progressbar(self, variable=self.progress_var, maximum=self.total).pack(fill='both')

	def loading(self, crawler):
		Thread(target=crawler.crawling).start()		
		while self.done != self.total:
			self.update()
			self.done = crawler.schedule[0]
			self.progress_var.set(self.done)
			self.prompt_text.set(f'正在下載頁面資料： {self.done: 3d}/{self.total: 3d}')
		self.destroy()

def loading_window(window, CrawlerType):
	try:
		window.crawler = CrawlerType()
		window.withdraw()
		ProgressWindow(window.crawler.schedule).loading(window.crawler)
	except requests.exceptions.ConnectionError:
		messagebox.showerror(title='連線錯誤', message='請確認與網際網路的連線')
		window.destroy()
	finally:
		window.deiconify()

class Analyze(tk.Toplevel):
	class SearchBar(tk.Frame):
		def __init__(self, parent, dates):
			super().__init__(parent)
			self.start_date = ttk.Combobox(self, values=dates, state='readonly')
			self.end_date = ttk.Combobox(self, values=dates, state='readonly')
			tk.Label(self, text='開始').grid(column=0, row=0)
			tk.Label(self, text='結束').grid(column=1, row=0)
			tk.Button(self, text='查詢', state=tk.NORMAL, command=parent.search).grid(column=2, row=0, rowspan=2, sticky=tk.NS)
			self.start_date.grid(column=0, row=1)
			self.end_date.grid(column=1, row=1)

	class InfoTab(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)
		def display_chart(self, cnt):
			try:
				self.pie.destroy()
			except AttributeError:
				pass
			fig = PieChart(cnt)
			self.pie = FigureCanvasTkAgg(fig, self).get_tk_widget()
			self.pie.pack()

	def __init__(self):
		super().__init__()
		self.title('歷年發票特別獎、特獎分析')
		loading_window(self, AnalyzeCrawler)
		self.search_bar = self.SearchBar(self, self.crawler.dates)
		self.search_bar.pack()
		self.nb = ttk.Notebook(self)
		self.tabs = { name: self.InfoTab(self.nb) for name in self.crawler.titles }
		for tab, title in zip(self.tabs.values(), self.crawler.titles):
			self.nb.add(tab, text=title)
		self.nb.pack(fill='both')

	def search(self):
		beg = self.search_bar.start_date.get()
		end = self.search_bar.end_date.get()
		try:
			for tab, info in zip(self.tabs.values(), self.crawler.get_date_range_info(beg, end)):
				tab.display_chart(info)
		except ValueError:
			messagebox.showerror(title='開始或結束時間為空值', message='請選擇時間區段！')
		except IndexError:
			messagebox.showerror(title='時間區段錯誤', message='開始必須比結束來得早！')


class Redeem(tk.Toplevel):
	class SearchByInputTab(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)
			self.parent = parent
			self.years_selector = ttk.Combobox(self, values=parent.crawler.years, state='readonly')
			self.months_selector = ttk.Combobox(self, values=['{:02d} ~ {:02d} 月'.format(i-1, i) for i in range(12, 1, -2)], state='readonly')
			self.history = tk.Listbox(self)
			self.entry = tk.Entry(self)
			self.entry.bind('<KP_Enter>', self.search)
			self.entry.bind('<Return>', self.search)
			tk.Label(self, text='選擇年份').grid(column=0, row=0)
			tk.Label(self, text='選擇月份').grid(column=1, row=0)
			self.years_selector.grid(column=0, row=1)
			self.months_selector.grid(column=1, row=1)
			self.history.grid(column=0, row=2, columnspan=2, sticky=tk.EW)
			self.entry.grid(column=0, row=3, columnspan=2, sticky=tk.EW)
			tk.Button(self, text='只顯示中獎發票', command=lambda: parent.winning_only(self.history)).grid(column=0, row=4, columnspan=2, sticky=tk.EW)

		def search(self, event):
			number = self.entry.get()
			try:
				price = self.parent.crawler.get_price(number, self.years_selector.get(), int(self.months_selector.get().split()[0]))
			except IndexError:
				messagebox.showerror(title='沒有日期', message='請輸入要查詢的日期')
			except KeyError:
				messagebox.showerror(title='日期錯誤', message='還沒有該日期的發票資訊')
			else:
				self.history.insert(tk.END, '{}: {:>} 元'.format(number, price))
				self.history.yview(tk.END)
			finally:
				self.entry.delete(0, tk.END)

	class SearchFromFileTab(tk.Frame):
		def __init__(self, parent):
			super().__init__(parent)
			self.parent = parent
			self.invoices = tk.Listbox(self)
			self.filepath = tk.Entry(self, text='')
			self.filepath.grid(column=0, row=0, sticky=tk.EW, ipadx=40)
			tk.Button(self, text='選擇檔案...', command=self.open_file).grid(column=1, row=0)
			tk.Button(self, text='查詢', command=self.search).grid(column=2, row=0, sticky=tk.EW)
			self.invoices.grid(column=0, row=1, columnspan=3, sticky=tk.EW)
			tk.Button(self, text='只顯示中獎發票', command=lambda: parent.winning_only(self.invoices)).grid(column=0, row=2, columnspan=3, sticky=tk.EW)

		def open_file(self):
			filepath = filedialog.askopenfilename(initialdir='.', title='Select file', filetypes=(('csv files', '*.csv'),))
			self.filepath.delete(0, tk.END)
			self.filepath.insert(0, filepath)

		def search(self):
			invoice_buf = {}
			try:
				with open(self.filepath.get(), 'r') as file:
					table = csv.DictReader(file)
					for invoice_info in table:
						for date, number in invoice_info.items():
							if number:
								year, month = date.split('/')
								invoice = '{}: {:>} 元'.format(number,
									self.parent.crawler.get_price(number, year, int(month))) 
								try:
									invoice_buf[date].append(invoice)
								except KeyError:
									invoice_buf[date] = [invoice]
			except FileNotFoundError:
				messagebox.showerror(title='無法開啟檔案', message='請選擇要開啟的檔案')
			else:
				self.invoices.delete(0, tk.END)
				for date, numbers in sorted(invoice_buf.items(), key=lambda x: x[0]):	
					for number in sorted(numbers, key=lambda x: int(x.split()[-2]), reverse=True):
						self.invoices.insert(tk.END, date+': '+number)


	def __init__(self):
		super().__init__()
		self.title('發票兌獎')
		loading_window(self, RedeemCrawler)
		self.nb = ttk.Notebook(self)
		self.nb.add(self.SearchByInputTab(self), text='手動輸入')
		self.nb.add(self.SearchFromFileTab(self), text='從檔案讀入')
		self.nb.pack(fill='both')

	@staticmethod
	def winning_only(listbox):
		now = 0
		try:
			while True:
				if int(listbox.get(now).split()[-2]):
					now += 1
				else:
					listbox.delete(now)
		except IndexError:
			pass


class Menu(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title('統一發票')
		tk.Button(self, text='歷年特別獎、特獎分析', command=lambda : self.new_window(Analyze)).pack(fill='x')
		tk.Button(self, text='發票兌獎', command=lambda: self.new_window(Redeem)).pack(fill='x')
		
	def new_window(self, WindowType):
		self.withdraw()
		try:
			form = WindowType()
			self.wait_window(form)
		except tk.TclError:
			pass
		finally:
			self.deiconify()