import urllib2, time, threading, re, sys
from bs4 import BeautifulSoup

def findFirstClassRec(parent, tagt, classt):
	for tag in parent.find_all(tagt):
		try:
			if classt in tag["class"]:
				return tag
		except KeyError:
			pass

	print >> sys.stderr, "Could not find " + classt
	return None

def is_url_blacklisted(url):
	blacklist = [
		# Wrong formats
		"youtube.com",
		"imgur.com",
		"mediacru.sh",
		"pasteboard.co",
		".png",
		".html",
		"postimg.org",
		"lut.im",

		# Wrong links
		"forum.minetest.net/profile.php",
		"viewtopic.php",
		"creativecommons.org",
		"gnu.org",
		"sam.zoy.org",
		"wtfpl.net",
		"github.com/minetest/minetest",
		"wiki.minetest.com",
		"wiki.minetest.net",
		"dev.minetest.net",

		# Dead sites
		"ubuntuone.com",
		"ompldr.org",
		"04.jp.org"
	]

	for item in blacklist:
		if item in url:
			return True

	return False

def validate_basename(s):
	basename_blacklist = ["mod", "modpack", "git", "github", "game", "subgame"]
	if s.lower() in basename_blacklist:
		return False

	all_number = True
	for c in s:
		if not c.isnumeric():
			all_number = False

		if not c.isalnum() and c != "-" and c != "_":
			return False

	if all_number:
		return False

	return True

def get_download(basename, content):
	possibles = []

	# Get indexes of download
	content_str_l = unicode(content).lower()
	idxs = [m.start() for m in re.finditer('download', content_str_l)]

	# Iterate through links
	for link in content.find_all("a"):
		url = link['href']
		if is_url_blacklisted(url):
			continue

		# Check for github link
		ghpat = re.compile(r'(github.com|gitorious.com|bitbucket.org|gitlab.com|repo.or.cz)/([A-Za-z0-9_\-]+)/([A-Za-z0-9_\-]+)')
		match = re.search(ghpat, url, flags=0)
		if match and match.group(1) and match.group(2) and match.group(3):
			if basename.lower() in match.group(3).strip().lower():
				return "https://" + match.group(1) + "/" + \
						match.group(2) + "/" + match.group(3) + "/"

		# Look for "download" on the link or around the link
		is_download = False
		idx = content_str_l.find(url)
		if "download" in link.text.lower():
			is_download = True
		else:
			for i in idxs:
				if idx - i < 30:
					is_download = True
					break

		if is_download and ("http" in url or "git" in url):
			possibles.append(url)

	if len(possibles) > 0:
		return possibles[0]
	else:
		return None

def do_work(url):
	# Download and parse
	handle = urllib2.urlopen(url)
	html = ""
	for line in handle:
		html += line
	soup = BeautifulSoup(html, 'html.parser')

	# Read title
	title = soup.title.text
	basename = None
	pattern = re.compile(r'\[([A-Za-z0-9_\- ]+)\]')
	for match in reversed(re.findall(pattern, title)):
		match = match.strip()
		if validate_basename(match):
			basename = match
			break

	if not basename:
		print >> sys.stderr, "\033[91mUnable to get basename from " + title + "\033[0m"
		return

	# Get post content
	post = findFirstClassRec(soup.find(id="page-body"), "div", "post")
	if not post:
		return

	author = findFirstClassRec(post, "p", "author")
	if not author:
		return
	name = author.find("strong")
	if not name:
		return

	content = findFirstClassRec(post, "div", "content")
	if not content:
		return

	# Get download
	download = get_download(basename, content)
	if download:
		return name.text + ", " + basename + ", " + download
	else:
		print >> sys.stderr, "\033[91mUnable to find a download for " +  basename + "\033[0m"
		return


print_lock = threading.Lock()
def parse_topic(url):
	res = do_work(url)
	if res:
		with print_lock:
			print(res)
	else:
		print >> sys.stderr, "\033[91m" + url + " failed!\033[0m"


threads = []
todo = []
g_start = 0
def populate_todo():
	global g_start, todo

	# Download and parse
	if g_start > 630:
		return False
	url = "https://forum.minetest.net/viewforum.php?f=11&start=" + str(g_start)
	g_start += 30
	handle = urllib2.urlopen(url)
	html = ""
	for line in handle:
		html += line.strip() + " "

	html = html.replace("</a> </a>", "</a>")
	soup = BeautifulSoup(html, 'html.parser')

	# Read title
	title = soup.title.text

	topics = None
	count = 0

	forumbg = None
	for tag in soup.find_all("div"):
		try:
			if "forumbg" in tag["class"] and not "announcement" in tag["class"]:
				forumbg = tag
				break
		except KeyError:
			pass
	if not forumbg:
		return False

	topics = findFirstClassRec(forumbg, "ul", "topics")
	if not topics:
		return False

	count = 0
	for tag in topics.find_all("li"):
		if not "sticky" in tag['class']:
			count = count + 1
			todo.append(tag.find("a")['href'].replace("./", "http://forum.minetest.net/"))

	print>> sys.stderr, "\033[94mAdded " + str(count) + " new topics to the todo list.\033[0m"

	return True

print("Author, Basename, URL")

while populate_todo():
	while len(todo) > 0:
		threads = [t for t in threads if t.is_alive()]

		if len(threads) < 10:
			url = todo.pop(0)
			t = threading.Thread(target=parse_topic, args=(url,))
			threads.append(t)
			t.start()
		else:
			time.sleep(0.1)

# Join threads and wait for completion
for t in threads:
	t.join()
