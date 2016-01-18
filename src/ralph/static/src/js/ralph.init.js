var ralph = ralph || {};
ralph.jQuery = jQuery.noConflict();

function dismissRelatedLookupPopup(win, chosenId) {
    var name = windowname_to_id(win.name);
/*
    var elem = document.getElementById(name);
    if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
        elem.value += ',' + chosenId;
    } else {
        document.getElementById(name).value = chosenId;
    }
*/

    console.log('name', name);
    var elem = document.querySelector('#' + name);
    elem.xxx(chosenId);
    win.close();
}


