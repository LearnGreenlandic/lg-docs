PRAGMA case_sensitive_like = ON;
PRAGMA foreign_keys = OFF;
PRAGMA journal_mode = MEMORY;
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA synchronous = OFF;
PRAGMA threads = 4;
PRAGMA trusted_schema = OFF;
PRAGMA page_size = 65536;
VACUUM;
PRAGMA locking_mode = NORMAL;


CREATE TABLE articles (
	a_id INTEGER NOT NULL,
	a_title TEXT NOT NULL,
	a_ref TEXT NOT NULL,
	a_ref_url TEXT NOT NULL,
	a_short TEXT NOT NULL,
	a_long TEXT NOT NULL,

	PRIMARY KEY (a_id AUTOINCREMENT)
);


CREATE TABLE lookups (
	l_id TEXT NOT NULL,
	l_dan INTEGER NOT NULL DEFAULT 0,
	l_eng INTEGER NOT NULL DEFAULT 0,
	l_kal INTEGER NOT NULL DEFAULT 0,

	PRIMARY KEY (l_id),

	FOREIGN KEY (l_dan) REFERENCES articles (a_id) ON UPDATE CASCADE,
	FOREIGN KEY (l_eng) REFERENCES articles (a_id) ON UPDATE CASCADE,
	FOREIGN KEY (l_kal) REFERENCES articles (a_id) ON UPDATE CASCADE
);
