from django import template

register = template.Library()

@register.simple_tag
def generic_table_sorter(table,field):
    curfield = table.sortfield
    direction = table.direction
    glyph = 'glyphicon-'
    if curfield==field:
        glyph += 'circle-'
    glyph += 'arrow-'
    if curfield==field and direction=='desc':
        glyph += 'up'
    else:
        glyph += 'down'
    if curfield==field and direction!='desc':
        direction = 'desc'
    else:
        direction = 'asc'
    return '<a href="'+table.params_subst_link({'sort' : field, 'direction' : direction})+'"><span class="glyphicon '+glyph+'"></span></a>'

