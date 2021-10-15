import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'tc-button-refresh',
  templateUrl: './button-refresh.component.html',
  styleUrls: ['./button-refresh.component.scss']
})
export class ButtonRefreshComponent {
  @Output()
  public readonly clickRefresh = new EventEmitter<void>();

  public onClickRefresh(): void{
    this.clickRefresh.emit()
  }
}

