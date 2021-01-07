import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
import requests
from Crawler import AnalyzeCrawler, Crawler
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

def loading_window(window):
	try:
		window.crawler = AnalyzeCrawler()
		progress = ProgressWindow(window.crawler.schedule)
		window.withdraw()
		progress.loading(window.crawler)
	except requests.exceptions.ConnectionError:
		messagebox.showerror(title='連線錯誤', message='請確認與網際網路的連線')
		window.destroy()
	finally:
		window.deiconify()

class Analyze(tk.Toplevel):
	def __init__(self):
		super().__init__()
		self.title('歷年發票特別獎、特獎分析')
		loading_window(self)
		self.search_bar = SearchBar(self, self.crawler.dates)
		self.search_bar.pack()
		self.nb = ttk.Notebook(self)
		self.tabs = { name: InfoTab(self.nb) for name in self.crawler.titles }
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
	def __init__(self):
		super().__init__()