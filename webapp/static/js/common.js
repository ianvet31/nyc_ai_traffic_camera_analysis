function getSelectedBoroughs(){return Array.from(document.querySelectorAll('.borough-filter:checked')).map(cb=>cb.value)}
function initBaseMap(){const map=L.map('map').setView([40.7128,-74.0060],12);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);return map}
function wireBoroughFilters(onChange){document.querySelectorAll('.borough-filter').forEach(cb=>cb.onchange=onChange)}

// Make a Leaflet popup draggable by its container
function makePopupDraggable(popup){
	const container = popup.getElement?.();
	if (!container) return;
	// Add a top drag handle that doesn't overlap resize handles or content
	let handle = container.querySelector('.popup-drag-handle');
	if (!handle) {
		handle = document.createElement('div');
		handle.className = 'popup-drag-handle';
		container.appendChild(handle);
	}
	let isDown=false, startX=0, startY=0, startLeft=0, startTop=0;
	const onMouseDown=(e)=>{
		isDown=true;
		startX=e.clientX; startY=e.clientY;
		const rect = container.getBoundingClientRect();
		// Switch to fixed positioning while preserving current screen position
		container.style.position='fixed';
		container.style.left = rect.left + 'px';
		container.style.top = rect.top + 'px';
		startLeft=rect.left; startTop=rect.top;
		e.preventDefault();
		e.stopPropagation();
	};
	const onMouseMove=(e)=>{
		if(!isDown) return;
		const dx=e.clientX-startX, dy=e.clientY-startY;
		container.style.left=(startLeft+dx)+'px';
		container.style.top=(startTop+dy)+'px';
	};
	const onMouseUp=()=>{isDown=false};
	handle.addEventListener('mousedown', onMouseDown);
	window.addEventListener('mousemove', onMouseMove);
	window.addEventListener('mouseup', onMouseUp);
}

// Generic draggable for any DOM element (position: fixed)
function makeDraggable(el, handle){
	const dragHandle = handle || el;
	if (!el || !dragHandle) return;
	let isDown=false, startX=0, startY=0, startLeft=0, startTop=0;
	const onMouseDown=(e)=>{
		// Ignore when starting near resize edges (8px)
		const rect = el.getBoundingClientRect();
		const margin = 10;
		if (e.clientX > rect.right - margin || e.clientY > rect.bottom - margin) return;
		isDown=true;
		startX=e.clientX; startY=e.clientY;
		startLeft=rect.left; startTop=rect.top;
		// Preserve current on-screen position before switching to fixed
		el.style.position='fixed';
		el.style.left = Math.round(rect.left) + 'px';
		el.style.top = Math.round(rect.top) + 'px';
		e.preventDefault();
	};
	const onMouseMove=(e)=>{
		if(!isDown) return;
		const dx=e.clientX-startX, dy=e.clientY-startY;
		el.style.left=Math.round(startLeft+dx)+'px';
		el.style.top=Math.round(startTop+dy)+'px';
	};
	const onMouseUp=()=>{isDown=false};
	dragHandle.addEventListener('mousedown', onMouseDown);
	window.addEventListener('mousemove', onMouseMove);
	window.addEventListener('mouseup', onMouseUp);
}
