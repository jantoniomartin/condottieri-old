function changed_code(box) {
	// id = id_form-$-code
	id_fields = box.id.split('-')
	//formid = box.id.charAt(8)
	formid = id_fields[1]
	code = box.value
	destination = document.getElementById('id_form-' + formid + '-destination')
	conversion = document.getElementById('id_form-' + formid + '-conversion')
	subunit = document.getElementById('id_form-' + formid + '-subunit')
	subcode = document.getElementById('id_form-' + formid + '-subcode')
	subdestination = document.getElementById('id_form-' + formid + '-subdestination')
	subconversion = document.getElementById('id_form-' + formid + '-subconversion')
	switch (code) {
		case 'H':
		case 'B':
			destination.style.display = 'none'
			conversion.style.display = 'none'
			subunit.style.display = 'none'
			subcode.style.display = 'none'
			subdestination.style.display = 'none'
			subconversion.style.display = 'none'
			break
		case '-':
			destination.style.display = 'block'
			conversion.style.display = 'none'
			subunit.style.display = 'none'
			subcode.style.display = 'none'
			subdestination.style.display = 'none'
			subconversion.style.display = 'none'
			break
		case '=':
			destination.style.display = 'none'
			conversion.style.display = 'block'
			subunit.style.display = 'none'
			subcode.style.display = 'none'
			subdestination.style.display = 'none'
			subconversion.style.display = 'none'
			break
		case 'C':
			destination.style.display = 'none'
			conversion.style.display = 'none'
			subunit.style.display = 'block'
			subcode.style.display = 'none'
			subdestination.style.display = 'block'
			subconversion.style.display = 'none'
			break
		case 'S':
			destination.style.display = 'none'
			conversion.style.display = 'none'
			subunit.style.display = 'block'
			subcode.style.display = 'block'
			subdestination.style.display = 'none'
			subconversion.style.display = 'none'
			break	
	}
}

function changed_subcode(box) {
	// id = id_form-$-subcode
	formid = box.id.charAt(8)
	code = box.value
	destination = document.getElementById('id_form-' + formid + '-subdestination')
	conversion = document.getElementById('id_form-' + formid + '-subconversion')
	switch (code) {
		case 'H':
		case 'B':
			destination.style.display = 'none'
			conversion.style.display = 'none'
			break
		case '-':
			destination.style.display = 'block'
			conversion.style.display = 'none'
			break
		case '=':
			destination.style.display = 'none'
			conversion.style.display = 'block'
			break
	}
}
