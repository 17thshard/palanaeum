$(function(){
    $('input.priv-switch').change(function(){
        let user_id = $(this).data('user-id');
        let priv = $(this).data('priv');
        let user_active = $(`input[data-user-id=${user_id}][data-priv='is_active']`);
        let user_staff = $(`input[data-user-id=${user_id}][data-priv='is_staff']`);
        let user_superuser = $(`input[data-user-id=${user_id}][data-priv='is_superuser']`);

        if ($(this).prop('checked')) {
            switch (priv) {
                case 'is_superuser':
                    user_staff.prop('checked', true);
                case 'is_staff':
                    user_active.prop('checked', true);
                    break;
                default:
                    break;
            }
        } else {
            switch (priv) {
                case 'is_active':
                    user_staff.prop('checked', false);
                case 'is_staff':
                    user_superuser.prop('checked', false);
                    break;
                default:
                    break;
            }
        }

        let data = {
            'user_id': user_id,
            'is_active': user_active.prop('checked'),
            'is_staff': user_staff.prop('checked'),
            'is_superuser': user_superuser.prop('checked'),
        };
        if (!confirm(gettext("Are you sure?"))) {
            return;
        }
        $.post(Palanaeum.ADMIN_USER_EDIT, data, function(ret){
            if (!ret['success']) {
                noty({text: gettext('Error, couldn\'t save changes!'), type: 'error'});
                return;
            }
            let user_id = ret['user_id'];

            if (ret['is_active']) {
                user_active.prop('checked', true).parent().addClass('positive-background');
            } else {
                user_active.prop('checked', false).parent().removeClass('positive-background');
            }

            if (ret['is_staff']) {
                user_staff.prop('checked', true).parent().addClass('positive-background');
            } else {
                user_staff.prop('checked', false).parent().removeClass('positive-background');
            }

            if (ret['is_superuser']) {
                user_superuser.prop('checked', true).parent().addClass('positive-background');
            } else {
                user_superuser.prop('checked', false).parent().removeClass('positive-background');
            }

            noty({text: 'Privileges changed!', type: 'success'});
        });
    })
});