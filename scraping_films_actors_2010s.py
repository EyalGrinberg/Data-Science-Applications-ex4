import requests
from bs4 import BeautifulSoup
import pandas as pd

film2actors = dict()

for year in range(2010, 2020):
  print(year)
  film2actors_year = dict()
  res = requests.get('https://en.wikipedia.org/wiki/List_of_American_films_of_' + str(year))
  soup = BeautifulSoup(res.text, "html.parser")
  
  tables = soup.find_all('table', class_='sortable')
  print(' %d tables found' % len(tables))
  
  for table in tables:
    for tr in table.find_all('tr'):
      tds = tr.find_all('td')
      if not tds:
        continue
      for i, td in enumerate(tds):
        if 'title=' in str(td):
          film = td.text.strip()
          if i + 3 < len(tds):
            genre = tds[i + 3].text.strip()
            if 'Documentary' not in genre:
              if year < 2017:
                actors = list(filter(lambda s: not s.startswith(','),
                                    tds[i + 2].stripped_strings))
              else:
                actors =  tds[i + 2].text.split(';')[-1].split(', ')
                actors = list(map(lambda s: s.strip(), actors))
              film2actors_year[film] = {'actors': actors, 'year': year}
              break
  print(' %d films found' % len(film2actors_year))
  film2actors.update(film2actors_year)
    
films = list(film2actors.keys())
actors = [fdata['actors'] for film, fdata in film2actors.items()]
years = [fdata['year'] for film, fdata in film2actors.items()]
films_actors_edgelist = pd.DataFrame({'film': films, 'actor': actors, 'year': years}).explode('actor')

print('shape before cleanup:',films_actors_edgelist.shape)

### cleanup
# some films have no actors
films_actors_edgelist.dropna(inplace=True)

# some actors in spite of our efforts end with a comma
def strip_s(s):
  return s[:-1] if s.endswith(',') else s
films_actors_edgelist['actor'] = films_actors_edgelist.apply(lambda s: strip_s(s['actor']), axis=1)

# bad patterns, in spite of our efforts
for pattern in ['\.', 'and', '\(', '\n', '[222]', '\)', ',', 'Documentary', 'Family']:
  remove_rows = films_actors_edgelist['actor'].str.contains(pattern, na=False)
  print('pattern %s: removing %d rows' % (pattern, remove_rows.sum()))
  films_actors_edgelist = films_actors_edgelist[~remove_rows]
films_actors_edgelist = films_actors_edgelist[films_actors_edgelist['actor'] != ' ']

print('shape after cleanup:',films_actors_edgelist.shape)

# sink to CSV
films_actors_edgelist.to_csv('data/films_actors_edgelist_2010s.csv')
