import { Component, Input, Output, EventEmitter } from '@angular/core';

interface ICollection {
  title: string;
  property: string;
  property_lv2?: string;
  type?: 'string' | 'array-length' | IPropertyInObjects | IPropertyBoolean;
  class?: 'name-start';
  icon?: string;
}

interface IPropertyInObjects {
  propertyDepend: string;
  typeDepend: 'propertyInObjectsInArray';
}

interface IPropertyBoolean {
  propertyDepend: string[];
  typeDepend: 'boolean';
}

@Component({
  selector: 'vdi-table-component',
  templateUrl: './table-component.component.html',
  styleUrls: ['./table-component.component.scss']
})
export class TableComponentComponent {
  @Input() entity: string | undefined;
  @Input() data: object[] = [];
  @Input() collection: ICollection[] = [];
  @Input() cursor: boolean = false;
  @Output() clickRowData: EventEmitter<object> = new EventEmitter<object>();
  @Output() sortListNow: EventEmitter<object> = new EventEmitter<object>();

  public titleSort: string;
  public sort: boolean = false;
  public ordering: string;

  constructor() {}

  public clickRow(item: object) {
    this.clickRowData.emit(item);
  }

  public sortList(objFromCollection: {property: string, sort: boolean}) {
    if (this.ordering !== objFromCollection.property) {
      objFromCollection.sort = false;
    }
    this.ordering = objFromCollection.property;
    objFromCollection.sort = !objFromCollection.sort;
    if (objFromCollection.sort) {
      this.sortListNow.emit({nameSort: objFromCollection.property, reverse: false, spin: true });
    } else {
      this.sortListNow.emit({nameSort: objFromCollection.property, reverse: true, spin: true });
    }
  }

  public setSortName(name) {
    this.titleSort = `Нажмите для сортировки по полю ${name}`;
  }

  // set sortName(name) {
  //   this.sortName = `Сортировать по полю ${name}`;
  // }
     // опровобовать при OnPush
  // get sortName() {
  //   return this.sortName;
  // }

}
