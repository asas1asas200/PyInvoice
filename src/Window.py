import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import requests
from Crawler import AnalyzeCrawler
from Chart import PieChart

class SearchBar(tk.Frame):
	def __init__(self, parent, dates):
		super().__init__(parent)
		self.start_label = tk.Label(self, text='開始')
		self.end_label = tk.Label(self, text='結束')
		self.start_date = ttk.Combobox(self, values=dates, state='readonly')
		self.end_date = ttk.Combobox(self, values=dates, state='readonly')
		self.search_button = tk.Button(self, text='查詢', state=tk.NORMAL, command=parent.search)
		self.start_label.grid(column=0, row=0)
		self.end_label.grid(column=1, row=0)
		self.start_date.grid(column=0, row=1)
		self.end_date.grid(column=1, row=1)
		self.search_button.grid(column=2, row=0, rowspan=2, sticky=[tk.N, tk.S])

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

class Analyze(tk.Toplevel):
	def __init__(self):
		super().__init__()
		self.title('歷年發票特別獎、特獎分析')
		try:
			self.crawler = AnalyzeCrawler()
			self.loading()
		except requests.exceptions.ConnectionError:
			messagebox.showerror(title='連線錯誤', message='請確認與網際網路的連線')
			self.destroy()
		else:
			self.search_bar = SearchBar(self, self.crawler.dates)
			self.search_bar.pack()
			self.nb = ttk.Notebook(self)
			self.tabs = { name: InfoTab(self.nb) for name in self.crawler.titles }
			for tab, title in zip(self.tabs.values(), self.crawler.titles):
				self.nb.add(tab, text=title)
			self.nb.pack(fill='both')

	def loading(self):
		popup = tk.Toplevel(self, takefocus=True)
		popup.title('下載中...')
		popup.resizable(0, 0)
		progress = self.crawler.schedule
		prompt_text = tk.StringVar()
		prompt_label = tk.Label(popup, textvariable=prompt_text)
		progress_var = tk.DoubleVar()
		progress_bar = ttk.Progressbar(popup, variable=progress_var, maximum=progress[1])
		progress_bar.pack(fill='both')
		prompt_label.pack()
		self.withdraw()
		Thread(target=self.crawler.analyzing).start()
		while progress[0] != progress[1]:
			popup.update()
			progress = self.crawler.schedule
			progress_var.set(progress[0])
			prompt_text.set(f'正在下載頁面資料： {progress[0]:3d}/{progress[1]:3d}')
		self.deiconify()
		popup.destroy()


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
	def __init__(self):
		super().__init__()