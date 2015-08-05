import common, re, sys

def get_basename(soup, url):
	title = soup.title.text
	pattern = re.compile(r'\[([A-Za-z0-9_\- ]+)\]')
	for match in reversed(re.findall(pattern, title)):
		match = match.strip()
		if common.validate_basename(match):
			return match

	return None

pm = common.ParserManager("https://forum.minetest.net/viewforum.php?f=11")
pm.get_basename = get_basename
pm.max_start = 630
pm.run()
