jQuery.noConflict();
var $j=jQuery

function toggle_params() {
	var code = $j("#id_code").val()
	switch (code) {
		case 'H':
		case 'B':
			$j("#id_destination").parent().fadeOut('slow');
			$j("#id_type").parent().fadeOut('slow');
			$j("#id_subunit").parent().fadeOut('slow');
			$j("#id_subcode").parent().fadeOut('slow');
			$j("#id_subdestination").parent().fadeOut('slow');
			$j("#id_subtype").parent().fadeOut('slow');
			break;
		case '-':
			$j("#id_type").parent().fadeOut('slow');
			$j("#id_subunit").parent().fadeOut('slow');
			$j("#id_subcode").parent().fadeOut('slow');
			$j("#id_subdestination").parent().fadeOut('slow');
			$j("#id_subtype").parent().fadeOut('slow');
			$j("#id_destination").parent().fadeIn('slow');
			break;
		case '=':
			$j("#id_destination").parent().fadeOut('slow');
			$j("#id_subunit").parent().fadeOut('slow');
			$j("#id_subcode").parent().fadeOut('slow');
			$j("#id_subdestination").parent().fadeOut('slow');
			$j("#id_subtype").parent().fadeOut('slow');
			$j("#id_type").parent().fadeIn('slow');
			break;
		case 'C':
			$j("#id_destination").parent().fadeOut('slow');
			$j("#id_type").parent().fadeOut('slow');
			$j("#id_subcode").parent().fadeOut('slow');
			$j("#id_subtype").parent().fadeOut('slow');
			$j("#id_subunit").parent().fadeIn('slow');
			$j("#id_subdestination").parent().fadeIn('slow');
			break;
		case 'S':
			$j("#id_destination").parent().fadeOut('slow');
			$j("#id_type").parent().fadeOut('slow');
			$j("#id_subdestination").parent().fadeOut('slow');
			$j("#id_subtype").parent().fadeOut('slow');
			$j("#id_subunit").parent().fadeIn('slow');
			$j("#id_subcode").parent().fadeIn('slow');
			toggle_subparams();
			break;
	}
}

function toggle_subparams() {
	var code = $j("#id_subcode").val()
	switch (code) {
		case 'H':
			$j("#id_subdestination").parent().fadeOut('slow');
			$j("#id_subtype").parent().fadeOut('slow');
			break;
		case '-':
			$j("#id_subtype").parent().fadeOut('slow');
			$j("#id_subdestination").parent().fadeIn('slow');
			break;
		case '=':
			$j("#id_subdestination").parent().fadeOut('slow');
			$j("#id_subtype").parent().fadeIn('slow');
			break;
	}
}

function hideOptional() {
	$j("#id_destination").parent().hide();
	$j("#id_type").parent().hide();
	$j("#id_subunit").parent().hide();
	$j("#id_subcode").parent().hide();
	$j("#id_subdestination").parent().hide();
	$j("#id_subtype").parent().hide();
}

function addChangeHandlers() {
	$j("#id_code").change( toggle_params );
	$j("#id_subcode").change (toggle_subparams );
}

function deleteOrder(pk) {
	$j.getJSON(game_url + "/delete_order/" + pk, orderDeleted)
}

function orderDeleted(data) {
	var e_msg = '';

	if (data) {
		if (eval(data.bad)) {
			$j('#so_emsg').text("Error: Order could not be deleted. ").fadeIn("slow");
		} else {
			$j("#order_" + data.order_id).fadeOut('slow');
		}
	} else {
		$j('#so_emsg').text("Ajax error: no data received. ").fadeIn("slow");
	}
}

function processOrderJson(data) {
	var e_msg = '';
	if (data) {
		if (eval(data.bad)) {
			errors = eval(data.errs)
			for (field in errors) {
				if (field == '__all__') {
					$j("#emsg").html(errors[field]);
					$j("#emsg").fadeIn('slow');
				} else {
					$j('#id_' + field).parent().before(errors[field]);
				}
			}
		} else {
			var new_li = '<li id="order_' + data.pk + '">';
			new_li += data.new_order;
			new_li += ' (<a href="' + game_url + '/delete_order/';
			new_li += data.pk;
			new_li += '" class="delete_order">';
			new_li += delete_text;
			new_li += '</a>)</li>';
			$j(new_li).hide().appendTo("#sent_orders").fadeIn("slow");
			addClickHandlers();
		}
	} else {
		$j('#emsg').text("Ajax error: no data received. ").fadeIn("slow");
	}
}

function prepareForm() {
	var options = {
		url: game_url,
		dataType: 'json',
		success: processOrderJson,
		beforeSubmit: beforeForm
	};
	$j('#order_form').ajaxForm(options);
}

function beforeForm(formData, jqForm, options) {
	$j('.errorlist').remove();
	$j('#emsg').html('&nbsp;').hide();
}

function addClickHandlers() {
	$j('a.delete_order').click( function(e) {
		e.preventDefault();
		pk = $j(this).parent().attr("id").split('_')[1];
		deleteOrder(pk);
	});
}

$j(document).ready(function() {
	hideOptional();
	prepareForm();
	addClickHandlers();
	addChangeHandlers();
	});
