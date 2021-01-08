from threading import Thread
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox, ttk, filedialog
import tkinter as tk
import requests
from Crawler import AnalyzeCrawler, RedeemCrawler
from Chart import PieChart


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
			range_info = self.crawler.get_date_range_info(beg, end)
		except ValueError:
			messagebox.showerror(title='開始或結束時間為空值', message='請選擇時間區段！')
		except IndexError:
			messagebox.showerror(title='時間區段錯誤', message='開始必須比結束來得早！')
		else:
			for tab, info in zip(self.tabs.values(), range_info):
				tab.display_chart(info)


class Redeem(tk.Toplevel):
	class SearchByInputTab(tk.Frame):
		def __init__(self, parent, years):
			super().__init__(parent)
			self.parent = parent
			self.years_selector = ttk.Combobox(self, values=years, state='readonly')
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

		def search(self, event):
			number = self.entry.get()
			try:
				price = self.parent.crawler.get_price(number, self.years_selector.get(), int(self.months_selector.get().split()[0]))
			except IndexError:
				messagebox.showerror(title='沒有日期', message='請輸入要查詢的日期')
			except KeyError:
				messagebox.showerror(title='日期錯誤', message='還沒有該日期的發票資訊')
			else:
				self.history.insert(tk.END, '{}: {:>}元'.format(number, price))
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
			tk.Button(self, text='選擇檔案...', command=self.open_file).grid(column=1, row=0, sticky=tk.EW)
			self.invoices.grid(column=0, row=1, columnspan=2, sticky=tk.EW)

		def open_file(self):
			filepath = filedialog.askopenfilename(initialdir='.', title='Select file', filetypes=(('csv files', '*.csv'),))
			self.filepath.delete(0, tk.END)
			self.filepath.insert(0, filepath)

	def __init__(self):
		super().__init__()
		self.title('發票兌獎')
		loading_window(self, RedeemCrawler)
		self.nb = ttk.Notebook(self)
		input_tab = self.SearchByInputTab(self, self.crawler.years)
		self.nb.add(input_tab, text='手動輸入')
		self.nb.add(self.SearchFromFileTab(self), text='從檔案讀入')
		self.nb.pack(fill='both')