(function($){
    var mockedField = $('#suggest-widget').text();

    var mockedEvent = {
        preventDefault: function(){}
    };

    var getListItems = function($field) {
        return $('.suggest-list li:not(.template)', $field);
    };

    var beforeEach = function(that) {
        $(document).foundation();
        $('#qunit-fixture').append(mockedField);
        that.$field = $('.suggest-field-widget');
        that.widget = that.$field.autocomplete({watch: false}).data('autocomplete');
    };

    module('widgets', {
        beforeEach: function(assert) {
            beforeEach(this);
        }
    });

    test('suggest_editMode_on', function(assert) {
        this.widget.editMode(true);

        assert.ok(this.$field.hasClass('in-progress'));
        assert.ok(this.$field.hasClass('edit'));
    });

    test('suggest_editMode_off', function(assert) {
        this.widget.editMode(false);

        assert.notOk(this.$field.hasClass('edit'));
    });

    test('suggest_deleteItem_empty_query', function(assert) {
        this.widget.deleteItem(mockedEvent);

        assert.equal(this.widget.$queryInput.val(), '');
    });

    test('suggest_deleteItem_empty_target', function(assert) {
        this.widget.deleteItem(mockedEvent);

        assert.equal(this.widget.$target.val(), '');
    });

    test('suggest_getQuery', function(assert) {
        this.widget.$queryInput.val('some sentence');

        assert.equal(this.widget.getQuery(), 'some sentence');
    });

    test('suggest_addItemToList_one_item', function(assert) {
        var item = {__str__: 'Some asset', pk: 10};
        var items = getListItems(this.$field);
        assert.equal(items.length, 0);

        this.widget.addItemToList(item);
        items = getListItems(this.$field);

        assert.equal(items.length, 1);
        assert.equal($('.link', items[0]).text(), 'Some asset');
    });

    test('suggest_itemClick', function(assert) {
        var item = {__str__: 'Some asset', pk: 10};
        var event = $.extend(mockedEvent ,{
            target: $('.link', this.widget.addItemToList(item)),
        });

        this.widget.itemClick(event);

        assert.equal($('.title', this.widget.$currentItem).text(), 'Some asset');
    });

    test('suggest_clearSuggestList', function(assert) {
        this.widget.addItemToList({__str__: 'test 1', pk: 1});
        this.widget.addItemToList({__str__: 'test 2', pk: 2});
        this.widget.clearSuggestList(mockedEvent);

        var items = getListItems(this.$field);
        assert.equal(items.length, 0);
    });
}(jQuery));
