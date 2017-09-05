import re

SRV_MSG_RE_STR = r'(?P<stamp>\d+:\d+:\d+\.\d+)\s+\[(?P<origin>\w+)\]\s+(?P<type>\w+)\s+(?P<object>[^\-\s]+) - (?P<message>[^\n]+)\b'
msg_regex = re.compile(SRV_MSG_RE_STR)

MGR_OK_STATUS = 'tlsPolicy=ON'
WEB_OK_STATUS = 'now serving at'