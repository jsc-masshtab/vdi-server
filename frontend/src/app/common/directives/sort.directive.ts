import { OnInit, Input, Directive, HostListener, Output, EventEmitter, ViewContainerRef } from '@angular/core';

interface ICollection {
    title: string;
    property: string;
    property_lv2?: string; // data : { property : {property_lv2: value}}
    type?: 'string' | 'array-length' | 'time';
    class?: 'name-start'; // flex-start
    icon?: string;
    sort?: boolean; // наличие поля и (sortListNow)="sortList($event)" включит сортировку
}

@Directive({ selector: '[sort]', exportAs: 'sortEl'})

export class SortDirective implements OnInit {

    @Input('sort') activeEl: ICollection;
    @Output() sortListNow: EventEmitter<object> = new EventEmitter<object>();

    public titleSort: string = '';
    // private orderingSort: string;

    constructor(private hostElement: ViewContainerRef) {}

    @HostListener('mouseenter') onMouseEnter() {
        this.setSortName();
    }

    @HostListener('click') onMouseClick() {
        this.sortList();
    }

    ngOnInit() {
        console.log(this.hostElement);
    }

    public setSortName() {
        if (this.activeEl.sort === undefined) {
            this.titleSort = '';
            return;
        }
        this.titleSort = `Нажмите для сортировки по полю ${this.activeEl.title}`;
    }

    public sortList() {
        if (this.activeEl.sort === undefined) {
            return;
        }
        // if (this.orderingSort !== this.activeEl.property) {
        //     this.activeEl.sort = true;
        // }
        // this.orderingSort = this.activeEl.property;

        this.activeEl.sort = !this.activeEl.sort; // первый раз сделает false

        if (this.activeEl.sort) {
            this.sortListNow.emit({nameSort: this.activeEl.property, spin: true });
        } else {
            this.sortListNow.emit({nameSort: `-${this.activeEl.property}`, spin: true });
        }
    }
}

// (click)="sortList(obj)" [title]="titleSort" (mouseenter)="setSortName(obj)" [class.cursorTrue]="obj.reverse_sort !== undefined"

// <span class="icon-sort" *ngIf="orderingSort === obj.property">
// <fa-icon [icon]="['fas','chevron-circle-up']" size="s" rotate="180" *ngIf="!obj.reverse_sort"></fa-icon>
// <fa-icon [icon]="['fas','chevron-circle-up']" size="s"  *ngIf="obj.reverse_sort"></fa-icon>
// </span> 