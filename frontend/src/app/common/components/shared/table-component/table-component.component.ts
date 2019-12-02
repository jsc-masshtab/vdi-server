import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
// @ts-ignore: Unreachable code error
import * as moment from 'moment';

interface ICollection {
  title: string;
  property: string;
  property_lv2?: string; // data : { property : {property_lv2: value}}
  type?: 'string' | 'array-length' | IPropertyInObjects | IPropertyBoolean | 'time';
  class?: 'name-start'; // flex-start
  icon?: string;
  reverse_sort?: boolean; // наличие поля и (sortListNow)="sortList($event)" включит сортировку
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
export class TableComponentComponent implements OnInit {
  @Input() entity: string | undefined;
  @Input() data: object[] = [];
  @Input() collection: ICollection[] = [];
  @Input() cursor: boolean = false;
  @Output() clickRowData: EventEmitter<object> = new EventEmitter<object>();
  @Output() sortListNow: EventEmitter<object> = new EventEmitter<object>();

  // public titleSort: string;
  // public orderingSort: string;
  public moment: any;

  constructor() {}

  ngOnInit() {
    this.moment = moment;
  }

  public clickRow(item: object) {
    this.clickRowData.emit(item);
  }

  public sortList(sort) {
    this.sortListNow.emit(sort);
  }

}
