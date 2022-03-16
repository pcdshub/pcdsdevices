"""
html templates for use in elog post formatting
"""

collapse_list_head = """<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
.collapsible {
  background-color: #777;
  color: white;
  padding: 10px;
  width: 100%;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;
}

.collapsible:hover {
  background-color: #555;
}

.collapsible:after {
  content: '+';
  color: white;
  font-weight: bold;
  float: right;
  margin-left: 5px;
}

.active:after {
  content: "-";
}

.content {
  min-width: 100px;
  overflow-x: auto;
}

.parent,
.child {
  display: none;
  margin-left: 20px;
}

.parent.show,
.child.show {
  display: block;
}
</style>
</head>
<body>
"""

collapse_list_tail = """<script>
// manage +/- toggle
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
  });
}

// manage show/hide behavior
var allCollapsibles = document.querySelectorAll('.collapsible');
allCollapsibles.forEach( item => {
  item.addEventListener("click", function() {
     if(this.nextElementSibling.classList.contains('show')) {
       this.nextElementSibling.classList.remove('show')
     } else {
       this.nextElementSibling.classList.add('show')
     }
  });
});
</script>

</body>
</html>"""
