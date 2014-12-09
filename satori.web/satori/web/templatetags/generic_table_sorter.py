from django import template

register = template.Library()

@register.simple_tag
def generic_table_sorter(table,field):
    curfield = table.sortfield
    direction = table.direction
    tooltip = ""
    tooltip = "Order by this column"
    glyph = 'glyphicon-'
    if curfield==field:
        glyph += 'circle-'
        tooltip = "Click to reverse sort order"
    glyph += 'arrow-'
    if curfield==field and direction=='desc':
        glyph += 'up'
    else:
        glyph += 'down'
    if curfield==field and direction!='desc':
        direction = 'desc'
    else:
        direction = 'asc'
    return '<a data-toggle="tooltip" data-placement="top" title="'+tooltip+'"href="'+table.params_subst_link({'sort' : field, 'direction' : direction})+'"><span class="glyphicon '+glyph+'"></span></a>'

