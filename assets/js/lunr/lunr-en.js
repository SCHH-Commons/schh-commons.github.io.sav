---
layout: none
---

let idx = lunr(function () {
  this.field('title')
  this.field('excerpt')
  this.field('categories')
  this.field('tags')
  this.ref('id')

  this.pipeline.remove(lunr.trimmer)

  for (var item in store) {
    this.add({
      title: store[item].title,
      excerpt: store[item].excerpt,
      categories: store[item].categories,
      tags: store[item].tags,
      id: item
    })
  }
});

document.addEventListener('DOMContentLoaded', () => {
  
  // Close search screen with Esc key
  document.addEventListener('keyup', (e) => {
    if (e.keyCode === 27) {
      if (document.querySelector('.initial-content').classList.contains('is--hidden')) {
        document.querySelector('.search-content').classList.toggle('is--visible');
        document.querySelector('.initial-content').classList.toggle('is--hidden');
      }
    }
  });
  
  // Search toggle
  document.querySelector('.search__toggle').addEventListener('click', () => {
    document.querySelector('.search-content').classList.toggle('is--visible');
    document.querySelector('.initial-content').classList.toggle('is--hidden');
    // set focus on input
    setTimeout(function () { document.querySelector('.search-content input').focus(); }, 400);
  });

  document.querySelector('input#search').addEventListener('keyup',(evt) => {
    var resultdiv = document.querySelector('#results');
    var query = evt.target.value.toLowerCase();
    var result =
      idx.query(function (q) {
        query.split(lunr.tokenizer.separator).forEach(function (term) {
          q.term(term, { boost: 100 })
          if(query.lastIndexOf(" ") != query.length-1){
            q.term(term, {  usePipeline: false, wildcard: lunr.Query.wildcard.TRAILING, boost: 10 })
          }
          if (term != ""){
            q.term(term, {  usePipeline: false, editDistance: 1, boost: 1 })
          }
        })
      });
    resultdiv.innerHTML = '';
    resultdiv.insertAdjacentHTML(
        'afterbegin',
        '<p class="results__found">' + result.length + ' {{ site.data.ui-text[site.locale].results_found | default: "Result(s) found" }}</p>'
    );
    for (var item in result) {
      var ref = result[item].ref;
      if(store[ref].teaser){
        var searchitem =
          '<div class="list__item">'+
            '<article class="archive__item" itemscope itemtype="https://schema.org/CreativeWork">'+
              '<h2 class="archive__item-title" itemprop="headline">'+
                '<a href="'+store[ref].url+'" rel="permalink">'+store[ref].title+'</a>'+
              '</h2>'+
              '<div class="archive__item-teaser">'+
                '<img src="'+store[ref].teaser+'" alt="">'+
              '</div>'+
              '<p class="archive__item-excerpt" itemprop="description">'+store[ref].excerpt.split(" ").splice(0,20).join(" ")+'...</p>'+
            '</article>'+
          '</div>';
      }
      else{
    	  var searchitem =
          '<div class="list__item">'+
            '<article class="archive__item" itemscope itemtype="https://schema.org/CreativeWork">'+
              '<h2 class="archive__item-title" itemprop="headline">'+
                '<a href="'+store[ref].url+'" rel="permalink">'+store[ref].title+'</a>'+
              '</h2>'+
              '<p class="archive__item-excerpt" itemprop="description">'+store[ref].excerpt.split(" ").splice(0,20).join(" ")+'...</p>'+
            '</article>'+
          '</div>';
      }
      resultdiv.insertAdjacentHTML('beforeend', searchitem);    
    }
  });
});
