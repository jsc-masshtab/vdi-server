import { Component, OnInit, Input, Output, EventEmitter, OnChanges } from '@angular/core';

@Component({
  selector: 'vdi-pagination',
  templateUrl: './pagination.component.html',
  styleUrls: ['./pagination.component.scss']
})
export class PaginationComponent implements OnInit, OnChanges {

  @Input() limit: number = 100;
  @Input() count: number = 1;
  @Input() offset: number = 0;

  @Output() action = new EventEmitter();

  public pages: number = 1;
  public currentPage: number = 1;

  constructor() { }

  ngOnInit() {
  }

  ngOnChanges() {
    this.updatePage();

    if (this.currentPage > this.pages) {
      this.emitPrevPage(this.currentPage - this.pages);
    }
  }

  private updatePage(): void {
    let suffix = 1;

    if (this.count !== 0) {
      if (this.count % this.limit === 0) {
        suffix = 0;
      }
    }

    this.pages = Math.floor(this.count / this.limit) + suffix;

    this.currentPage = Math.floor(this.offset / this.limit) + 1;
  }

  public emitNextPage(): void {
    if (this.currentPage < this.pages) {
      this.action.emit({
        offset: this.currentPage * this.limit
      });
    }
  }

  public emitPrevPage(count = 1): void {
    if (this.currentPage > 1) {
      this.action.emit({
        offset: (this.currentPage - (count + 1)) * this.limit
      });
    }
  }
}
