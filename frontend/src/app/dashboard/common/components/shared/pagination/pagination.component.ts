import { Component, OnInit, Input, ChangeDetectionStrategy, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'vdi-pagination',
  templateUrl: './pagination.component.html',
  styleUrls: ['./pagination.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaginationComponent implements OnInit {

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
  }

  private updatePage(): void {
    let suffix = 1;

    if (this.count != 0) {
      if (this.count % this.limit == 0) {
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

  public emitPrevPage(): void {
    if (this.currentPage > 1) {
      this.action.emit({
        offset: (this.currentPage - 2) * this.limit
      });
    }
  }
}
