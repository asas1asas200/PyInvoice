import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from Crawler import Crawler	

class Filter(tk.Frame):
	def __init__(self, parent):
		self.crawler = Crawler()
		super().__init__(parent)
		self.start_label = tk.Label(self, text='開始')
		self.end_label = tk.Label(self, text='結束')
		self.start_date = ttk.Combobox(self, values=self.crawler.dates, state='readonly')
		self.end_date = ttk.Combobox(self, values=self.crawler.dates, state='readonly')
		self.search_button = tk.Button(self, text='查詢', state=tk.NORMAL, command=self.search)
		self.start_label.grid(column=0, row=0)
		self.end_label.grid(column=1, row=0)
		self.start_date.grid(column=0, row=1)
		self.end_date.grid(column=1, row=1)
		self.search_button.grid(column=2, row=0, rowspan=2, sticky=[tk.N, tk.S])

	def search(self):
		if self.start_date.get() == '' or self.end_date.get() == '':
			messagebox.showerror(title='開始或結束時間為空值', message='請選擇時間區段！')
			return
		if self.start_date.get() > self.end_date.get():
			messagebox.showerror(title='時間區段錯誤', message='開始必須比結束來得早！')
			return
		print(self.crawler.get_date_range_info(self.start_date.get(), self.end_date.get()))

if __name__ == '__main__':
	root = tk.Tk()
	main = Filter(root)
	main.pack(fill='both', expand=True)
	root.mainloop()
