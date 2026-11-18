# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class DocChildItem(Item):
    parent_url = Field()
    chunk_index = Field()
    content = Field()
    embedding = Field()
    metadata = Field()
    
class DocItem(Item):
    url = Field()
    title = Field()
    section = Field()
    subsection = Field()
    content = Field()
    metadata = Field()


