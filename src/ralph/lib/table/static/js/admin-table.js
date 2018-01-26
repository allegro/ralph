document.addEventListener('DOMContentLoaded', function(){
  var admin_tables = document.querySelectorAll('.admin-table');
  admin_tables.forEach(function(table) {
    var expand = table.querySelector('.expand');
    var collapse = table.querySelector('.collapse');
    if(expand) {
        expand.addEventListener('click', function(){
            expand.closest('.control').classList.add('hide');
            collapse.closest('.control').classList.remove('hide');
            table.querySelectorAll('tr.can-hide').forEach(function(row){
              row.classList.remove('hide');
            });
        });
    }
    if(collapse) {
        collapse.addEventListener('click', function(){
            collapse.closest('.control').classList.add('hide');
            expand.closest('.control').classList.remove('hide');
              table.querySelectorAll('tr.can-hide').forEach(function(row){
              row.classList.add('hide');
            });
        });
    }
  });
}, false);
