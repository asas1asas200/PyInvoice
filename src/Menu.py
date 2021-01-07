import tkinter as tk
import Window

class Menu(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title('統一發票')
		self.btn_analyze = tk.Button(self, text='歷年特別獎、特獎分析', command=lambda : self.new_window(Window.Analyze))
		self.btn_redeem = tk.Button(self, text='發票兌獎', command=lambda: self.new_window(Window.Redeem))
		self.btn_analyze.pack(fill='x')
		self.btn_redeem.pack(fill='x')

	def new_window(self, WindowType):
		self.withdraw()
		try:
			form = WindowType()
			self.wait_window(form)
		except tk.TclError:
			pass
		finally:
			self.deiconify()

if __name__ == '__main__':
	root = Menu()
	root.mainloop()