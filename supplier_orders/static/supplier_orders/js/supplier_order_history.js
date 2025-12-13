(function(){
  // Fetch mock data from Django API or use fallback mock data
  const mockOrders = [
    {order_id:1001,date:'2025-11-02',supplier:'Acme Books',items:[{sku:'BK-001',title:'Intro to JS',qty:10,price:12.5}],total:125,status:'received'},
    {order_id:1002,date:'2025-11-15',supplier:'Pages & Co',items:[{sku:'BK-034',title:'Advanced CSS',qty:5,price:22}],total:110,status:'shipped'},
    {order_id:1003,date:'2025-12-01',supplier:'Acme Books',items:[{sku:'BK-002',title:'Python 101',qty:20,price:15}],total:300,status:'processing'},
    {order_id:1004,date:'2025-12-03',supplier:'Global Texts',items:[{sku:'BK-099',title:'Algorithms',qty:2,price:45}],total:90,status:'pending'},
    {order_id:1005,date:'2025-11-28',supplier:'Pages & Co',items:[{sku:'BK-076',title:'Design Patterns',qty:1,price:55}],total:55,status:'cancelled'},
    {order_id:1006,date:'2025-10-10',supplier:'Novelty Distributors',items:[{sku:'BK-121',title:'Modern Fiction',qty:12,price:8}],total:96,status:'received'},
    {order_id:1007,date:'2025-09-07',supplier:'Acme Books',items:[{sku:'BK-200',title:'Databases',qty:4,price:30}],total:120,status:'received'},
    {order_id:1008,date:'2025-12-04',supplier:'Global Texts',items:[{sku:'BK-132',title:'Networks',qty:3,price:40}],total:120,status:'shipped'},
    {order_id:1009,date:'2025-11-21',supplier:'Pages & Co',items:[{sku:'BK-140',title:'UX Basics',qty:7,price:18}],total:126,status:'processing'},
    {order_id:1010,date:'2025-11-30',supplier:'Novelty Distributors',items:[{sku:'BK-150',title:'Poetry',qty:6,price:10}],total:60,status:'pending'},
    {order_id:1011,date:'2025-12-05',supplier:'Acme Books',items:[{sku:'BK-170',title:'Machine Learning',qty:2,price:80}],total:160,status:'processing'},
    {order_id:1012,date:'2025-12-07',supplier:'Pages & Co',items:[{sku:'BK-177',title:'Cloud Eng',qty:1,price:95}],total:95,status:'pending'}
  ];

  // State
  let orders = mockOrders.slice();
  let filtered = orders.slice();
  let currentPage = 1; const pageSize = 6;
  const apiBase = '/api/supplier-orders';

  // Elements
  const tbody = document.querySelector('#ordersTable tbody');
  const supplierFilter = document.getElementById('supplierFilter');
  const statusFilter = document.getElementById('statusFilter');
  const searchInput = document.getElementById('searchInput');
  const pagination = document.getElementById('pagination');
  const exportCsvBtn = document.getElementById('exportCsv');
  const modal = document.getElementById('detailsModal');
  const modalContent = document.getElementById('modalContent');

  function init(){
    populateSupplierFilter();
    attachListeners();
    loadOrders();
  }

  function populateSupplierFilter(){
    const suppliers = Array.from(new Set(orders.map(o=>o.supplier))).sort();
    suppliers.forEach(s=>{
      const opt = document.createElement('option'); opt.value=s; opt.textContent=s; supplierFilter.appendChild(opt);
    });
  }

  function attachListeners(){
    supplierFilter.addEventListener('change',applyFilters);
    statusFilter.addEventListener('change',applyFilters);
    searchInput.addEventListener('input',debounce(applyFilters,200));
    exportCsvBtn.addEventListener('click',exportCSV);
    tbody.addEventListener('click',onTableClick);
    pagination.addEventListener('click',onPageClick);
    document.querySelector('.modal-close').addEventListener('click',()=>modal.close());
  }

  function loadOrders(){
    // Try to fetch from Django API, fallback to mock data
    const params = new URLSearchParams({page:1, pageSize:100});
    fetch(`${apiBase}/?${params}`)
      .then(r=>r.json())
      .then(data=>{
        orders = (data.data || []).map(o=>({
          order_id: o.order_id || o.id,
          date: o.date,
          supplier: o.supplier,
          items: o.items || [],
          total: o.total,
          status: o.status
        }));
        populateSupplierFilter();
        applyFilters();
      })
      .catch(e=>{
        console.log('Using fallback mock data', e);
        populateSupplierFilter();
        applyFilters();
      });
  }

  function applyFilters(){
    const supplier = supplierFilter.value.trim().toLowerCase();
    const status = statusFilter.value.trim().toLowerCase();
    const q = searchInput.value.trim().toLowerCase();
    filtered = orders.filter(o=>{
      if(supplier && o.supplier.toLowerCase() !== supplier) return false;
      if(status && o.status.toLowerCase() !== status) return false;
      if(!q) return true;
      const hay = [o.order_id,o.supplier,o.date,o.items.map(i=>i.sku+' '+i.title).join(' ')].join(' ').toLowerCase();
      return hay.indexOf(q)!==-1;
    });
    currentPage = 1;
    renderTable();
  }

  function renderTable(){
    tbody.innerHTML='';
    const start = (currentPage-1)*pageSize; const page = filtered.slice(start,start+pageSize);
    page.forEach(o=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>#${o.order_id}</td>
        <td>${o.date}</td>
        <td>${escapeHtml(o.supplier)}</td>
        <td>${o.items.length} item${o.items.length>1?'s':''}</td>
        <td>$${o.total.toFixed(2)}</td>
        <td><span class="status-badge status-${o.status}">${capitalize(o.status)}</span></td>
        <td class="actions"><button data-action="view" data-id="${o.order_id}">View</button></td>
      `;
      tbody.appendChild(tr);
    });
    renderPagination();
  }

  function renderPagination(){
    pagination.innerHTML='';
    const total = Math.ceil(filtered.length / pageSize) || 1;
    const prev = document.createElement('button'); prev.textContent='Prev'; prev.disabled = currentPage<=1; prev.dataset.page = currentPage-1; pagination.appendChild(prev);
    const info = document.createElement('span'); info.style.padding='6px 10px'; info.textContent = `Page ${currentPage} of ${total}`; pagination.appendChild(info);
    const next = document.createElement('button'); next.textContent='Next'; next.disabled = currentPage>=total; next.dataset.page = currentPage+1; pagination.appendChild(next);
  }

  function onPageClick(e){
    const btn = e.target.closest('button'); if(!btn || !btn.dataset.page) return; const p = Number(btn.dataset.page); if(!isNaN(p)){ currentPage = p; renderTable(); }
  }

  function onTableClick(e){
    const btn = e.target.closest('button'); if(!btn) return; const action = btn.dataset.action; const id = Number(btn.dataset.id);
    if(action==='view') showDetails(id);
  }

  function showDetails(orderId){
    const o = orders.find(x=>x.order_id===orderId); if(!o) return;
    modalContent.innerHTML = `
      <h2>Order #${o.order_id}</h2>
      <p><strong>Date:</strong> ${o.date}</p>
      <p><strong>Supplier:</strong> ${escapeHtml(o.supplier)}</p>
      <p><strong>Status:</strong> <span class="status-badge status-${o.status}">${capitalize(o.status)}</span></p>
      <h3>Items</h3>
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr><th>SKU</th><th>Title</th><th>Qty</th><th>Price</th></tr></thead>
        <tbody>
          ${o.items.map(i=>`<tr><td>${i.sku}</td><td>${escapeHtml(i.title)}</td><td>${i.qty}</td><td>$${i.price.toFixed(2)}</td></tr>`).join('')}
        </tbody>
      </table>
      <p style="margin-top:8px"><strong>Total:</strong> $${o.total.toFixed(2)}</p>
    `;
    if(typeof modal.showModal === 'function') modal.showModal();
  }

  function exportCSV(){
    const rows = [['order_id','date','supplier','items','total','status']];
    filtered.forEach(o=>{
      const items = o.items.map(i=>`${i.sku}:${i.qty}`).join('|');
      rows.push([o.order_id,o.date,o.supplier,items,o.total.toFixed(2),o.status]);
    });
    const csv = rows.map(r=>r.map(cell=>`"${String(cell).replace(/"/g,'""')}"`).join(',')).join('\n');
    const blob = new Blob([csv],{type:'text/csv;charset=utf-8;'});
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download='supplier_orders.csv'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  // Helpers
  function capitalize(s){return s.charAt(0).toUpperCase()+s.slice(1)}
  function escapeHtml(s){ return (s+'').replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c]; }); }
  function debounce(fn,ms){let t; return function(){clearTimeout(t); t=setTimeout(()=>fn.apply(this,arguments),ms)} }

  // Init
  init();
})();
