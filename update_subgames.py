import common, re



def get_basename(soup, url):
	title = soup.title.text
	pattern = re.compile(r'\[([A-Za-z0-9_\- ]+)\]')
	for match in reversed(re.findall(pattern, title)):
		match = match.strip()
		if common.validate_basename(match):
			return match

	title = title.lower().replace("[game]", "")
	title = title.replace("- minetest forums", "")
	#title = title.replace("minetest", "")
	title = title.split("[", 1)[0]
	title = title.split(":", 1)[0]
	title = title.split("- ", 1)[0]
	#title = re.sub(r'\[[^\]]*\]', '', title)
	title = re.sub(r'\([^\)]*\)', '', title).strip()
	title = title.replace(" ", "_")

	if title == "minetest_nostalgia":
		return "nostalgia"
	if title == "m13's_minecraft_classic_for_minetest":
		return "minecraft_classic"

	if common.validate_basename(title):
		return title
	else:
		return None

pm = common.ParserManager("https://forum.minetest.net/viewforum.php?f=15")
pm.max_start = 30
pm.get_basename = get_basename
pm.run()
