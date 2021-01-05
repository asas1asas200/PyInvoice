import tkinter as tk
import Window

class Menu(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title('統一發票')
		self.btn_analyze = tk.Button(self, text='歷年特別獎、特獎分析', command=self.analyze)
		self.btn_analyze.pack()
	def analyze(self):
		self.withdraw()
		form = Window.MainWindow()
		try:		
			self.wait_window(form)
		except tk.TclError:
			pass
		finally:
			self.deiconify()

if __name__ == '__main__':
	root = Menu()
	root.mainloop()