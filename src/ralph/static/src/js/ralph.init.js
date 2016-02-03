var ralph = ralph || {};
ralph.jQuery = jQuery.noConflict();

//TODO:: many adds: rack+server-room+data-center
//TODO:: check if auto-complete could adopt original django flow of `change`, `add`, `search`
function getCallerNode(win) {
    console.log('getCallerNode', win);
    var name = windowname_to_id(win.name);
    var elem = document.querySelector('#' + name);
    return elem;
}
function dismissRelatedLookupPopup(win, chosenId) {
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
        elem.value += ',' + chosenId;
    } else if (elem.nodeName.toUpperCase() === 'AUTO-COMPLETE') {
        elem.updateById(chosenId);
    } else {
        document.getElementById(name).value = chosenId;
    }
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

function dismissAddRelatedObjectPopup(win, newId, newRepr) {
    // newId and newRepr are expected to have previously been escaped by
    // django.utils.html.escape.
    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    var o;
    if (elem.nodeName.toUpperCase() === 'AUTO-COMPLETE') {
        //TODO:: change proto to something better
        console.log('proto')
        //elem = getCallerNode(win);
        elem.updateById(newId);
    } else if (elem) {
        console.log('non-proto')
        var elemName = elem.nodeName.toUpperCase();
        if (elemName == 'SELECT') {
            o = new Option(newRepr, newId);
            elem.options[elem.options.length] = o;
            o.selected = true;
        } else if (elemName == 'INPUT') {
            if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
                elem.value += ',' + newId;
            } else {
                elem.value = newId;
            }
        }
        // Trigger a change event to update related links if required.
        django.jQuery(elem).trigger('change');
    } else {
        var toId = name + "_to";
        o = new Option(newRepr, newId);
        SelectBox.add_to_cache(toId, o);
        SelectBox.redisplay(toId);
    }
    win.close();
}

function hideSuggestions(evt, obj) {
    var elems = document.querySelectorAll('auto-complete');
    if (!evt.target.classList.contains("auto-complete")) {
        // clicked outside auto-complete -> hide suggestions
        for(i=0; i<elems.length; i++) {
            elems[i].hideMenu = true;
        }
    }
}
window.addEventListener("click", hideSuggestions);
