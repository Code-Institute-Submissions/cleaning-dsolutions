$(document).ready(function() {
    $('#myTable').DataTable({
        "responsive": true,
        "paging":   true,
        "searching": true,
        "ordering": true,
        "info":     true,
        "stateSave": true
    });
} );

$("myTable").on("click", function(event){
  event.preventDefault()
});

$("#myTable").on("click", function(){alert('x')} )

// $("tr.myTable").click(function() {
// var tableData = $(this).children("td").map(function() {
//     return $(this).text();

//     })
// alert(tableData)
// })

// $('#myTable tbody').on('click','tr',function*(){
// alert(this);



//     
//         
//     

//   $("#myTable tbody").on("click", "tr", function () {
// 	var dataString = $(this).attr('data');
//     alert(dataString);
    
//     // var data = table.row(this).data();
//     // alert("You clicked on " + data[0] + "'s row");
//   });

if (document.getElementById('myTable2')) {
    $('#myTable2').DataTable({
        "responsive": true,
        "paging":   false,
        "searching": false,
        "ordering": false,
        "info":     false
    } );
}
