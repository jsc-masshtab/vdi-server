import { Component, Input, Output, EventEmitter, OnInit, HostBinding, OnChanges } from '@angular/core';
// @ts-ignore: Unreachable code error
import * as moment from 'moment';


interface ICollection {
  title: string;
  property: string | 'index-array';
  property_lv2?: string; // data : { property : {property_lv2: value}}
  type?: 'string' | 'array-length' | IPropertyInObjects | IPropertyBoolean | 'time' | 'array-type';
  class?: 'name-start'; // flex-start
  icon?: string;
  sort?: boolean; // наличие поля и (sortListNow)="sortList($event)" включит сортировку
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
export class TableComponentComponent implements OnInit, OnChanges {
  @Input() entity: string | undefined;
  @Input() data: object[] = [];
  @Input() collection: ICollection[] = [];
  @Input() cursor: boolean = false;
  @Output() clickRowData: EventEmitter<object> = new EventEmitter<object>();
  @Output() sortListNow: EventEmitter<object> = new EventEmitter<object>();

  @HostBinding('style.height') @Input() height = '100%'

  public exist_keys: string[] = []

  public titleSort: string;
  public orderingSort: string;

  public moment: any;

  constructor() { }

  ngOnInit() {
    this.moment = moment;    
  }

  ngOnChanges() {
    if (this.data) {
      if (this.data.length) {
        this.exist_keys = Object.keys(this.data[0]);
      }
    }
  }

  public clickRow(item: object) {
    this.clickRowData.emit(item);
  }

  public sortList(activeEl: ICollection) {
    if (activeEl.sort === undefined) {
      return;
    }
    if (this.orderingSort !== activeEl.property) {
      activeEl.sort = true;
    }
    this.orderingSort = activeEl.property;

    activeEl.sort = !activeEl.sort; // первый раз сделает false

    if (activeEl.sort) {
      this.sortListNow.emit({ nameSort: `-${activeEl.property}`, spin: true });
    } else {
      this.sortListNow.emit({ nameSort: activeEl.property, spin: true });
    }
  }

  public setSortName(activeEl: ICollection) {
    if (activeEl.sort === undefined) {
      this.titleSort = '';
      return;
    }
    this.titleSort = `Нажмите для сортировки по полю ${activeEl.title}`;
  }

  isExist(key) {
    if (key === 'index-array') {
      return true;
    }

    return this.exist_keys.includes(key);
  }

  parseNothing(obj, item) {
    if (obj.property_lv2) {
      return typeof item[obj.property][obj.property_lv2] === 'number' ? 0 : '--';
    } else if (obj.property) {
      return typeof item[obj.property] === 'number' ? 0 : '--';
    } else {
      return '--';
    }
  }

  formatBytes(bytes, delimiter = 'Байт', decimals = 3) {
    if (bytes === 0) { return '0 Байт'; }

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Байт', 'Кб', 'Мб', 'Гб', 'Тб', 'Пб', 'Эб', 'Зб', 'Йб'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const def = sizes.findIndex(size => size === delimiter);

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i + def];
  }
}
