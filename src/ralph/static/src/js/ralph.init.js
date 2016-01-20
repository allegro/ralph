var ralph = ralph || {};
ralph.jQuery = jQuery.noConflict();

function getCallerNode(win) {
    console.log('getCallerNode', win);
    var name = windowname_to_id(win.name);
    var elem = document.querySelector('#' + name);
    return elem;
}
function dismissRelatedLookupPopup(win, chosenId) {
/*
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
        elem.value += ',' + chosenId;
    } else {
        document.getElementById(name).value = chosenId;
    }
*/
    elem = getCallerNode(win);
    elem.updateById(chosenId);
    win.close();
}


function dismissChangeRelatedObjectPopup(win, objId, newRepr, newId) {
/*
    objId = html_unescape(objId);
    xnewRepr = html_unescape(newRepr);
    var id = windowname_to_id(win.name).replace(/^edit_/, '');
    var selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
    var selects = django.jQuery(selectsSelector);
    selects.find('option').each(function() {
        if (this.value === objId) {
            this.innerHTML = xnewRepr;
            this.value = newId;
        }
    });
    debugger;
*/
    elem = getCallerNode(win);
    elem.reloadBadges();
    win.close();
}

