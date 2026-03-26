def Split(x):
	x = x.split(",")
	school = x[0].replace("我是","")
	print(f"學校:{x[0]}")
	print(f"姓名:{x[2]}")


if __name__ == "__main__":

	Name = "我是靜宜大學,資管系二B,鄭姿佳"
	Split(Name)