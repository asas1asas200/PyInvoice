import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.font_manager import FontProperties
from pyparsing import col
from Crawler import Crawler	
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
		fig = PieChart(cnt)
		pie = FigureCanvasTkAgg(fig, self).get_tk_widget()
		pie.pack()

class MainWindow(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title('歷年發票特別獎、特獎分析')
		self.crawler = Crawler()
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

if __name__ == '__main__':
	root = MainWindow()
	root.mainloop()