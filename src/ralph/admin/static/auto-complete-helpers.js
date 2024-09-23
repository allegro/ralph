function getCallerNode(win) {
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
    elem = getCallerNode(win);
    elem.reloadBadges();
    win.close();
}

function dismissAddRelatedObjectPopup(win, newId, newRepr) {
    // newId and newRepr are expected to have previously been escaped by
    // django.utils.html.escape.
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    var o;
    var elemName = elem.nodeName.toUpperCase();
    if (elemName === 'AUTO-COMPLETE') {
        elem.updateById(newId);
    } else if (elem) {
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
        } else if (elemName == 'UL') {
            // If you don't have element, pass
            var item = elem.querySelector("li").cloneNode(true);
            var input = item.querySelector("input");
            input.setAttribute("value", newId);
            var label = item.querySelector("label");
            // <input name="abc" /> foo -> <input name="abc" /> bar
            label.innerHTML = label.innerHTML.replace(label.textContent, " " + newRepr);
            elem.appendChild(item);
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
    //TODO: this could be replaced by on-blur on auto-complete
    var elems = document.querySelectorAll('auto-complete');
    if (!evt.target.classList.contains("auto-complete")) {
        // clicked outside auto-complete -> hide suggestions
        for(i=0; i<elems.length; i++) {
            elems[i].hideMenu = true;
        }
    }
}
window.addEventListener("click", hideSuggestions);
