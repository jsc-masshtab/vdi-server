import { Component, OnInit, Input, OnChanges} from '@angular/core';

@Component({
  selector: 'vdi-table-component',
  templateUrl: './table-component.component.html',
  styleUrls: ['./table-component.component.scss']
})
export class TableComponentComponent implements OnChanges {

  @Input() data: object[] = [];
	@Input() collection: Set<object> = new Set();

  constructor() {}

  ngOnChanges() {

   for (let item of this.collection) {
     let a = item;
      console.log(a,'kjfkfkf',this.collection);
    }
   // console.log(this.data,this.collection);
  }

}
