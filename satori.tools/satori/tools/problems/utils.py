import re
import unicodedata

def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = re.sub('[^\w\s-]', '', s).strip().lower()
    s = re.sub('[-\s]+', '-', s)
    return s

