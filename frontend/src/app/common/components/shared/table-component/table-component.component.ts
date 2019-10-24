import { Component, Input, Output, EventEmitter } from '@angular/core';

interface ICollection {
  title: string;
  property: string;
  property_lv2?: string;
  type?: 'string' | 'array-length' | IPropertyInObjects | IPropertyBoolean;
  class?: 'name-start';
  icon?: string;
  reverse_sort: boolean; // включить сортировку наличие поля
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
  public orderingSort: string;

  constructor() {}

  public clickRow(item: object) {
    this.clickRowData.emit(item);
  }

  public sortList(objFromCollection: ICollection) {
    if (objFromCollection.reverse_sort === undefined) {
      return;
    }
    if (this.orderingSort !== objFromCollection.property) {
      objFromCollection.reverse_sort = true;
    }
    this.orderingSort = objFromCollection.property;

    objFromCollection.reverse_sort = !objFromCollection.reverse_sort; // первый раз сделает false

    if (objFromCollection.reverse_sort) {
      this.sortListNow.emit({nameSort: objFromCollection.property, reverse: true, spin: true });
    } else {
      this.sortListNow.emit({nameSort: objFromCollection.property, reverse: false, spin: true });
    }
  }

  public setSortName(objFromCollection: ICollection) {
    if (objFromCollection.reverse_sort === undefined) {
      this.titleSort = '';
      return;
    }
    this.titleSort = `Нажмите для сортировки по полю ${objFromCollection.title}`;
  }


  // set sortName(name) {
  //   this.sortName = `Сортировать по полю ${name}`;
  // }
     // опровобовать при OnPush
  // get sortName() {
  //   return this.sortName;
  // }

}
