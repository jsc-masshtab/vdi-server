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

  constructor() {}

  public clickRow(item: object) {
    this.clickRowData.emit(item);
  }

}
