import { Component, Input } from '@angular/core';

@Component({
  selector: 'vdi-tab',
  templateUrl: './tab.component.html',
  styleUrls: ['./tab.component.scss']
})
export class TabComponent {
  @Input() title: string;
  @Input() iconName: string
  @Input() active = false;

  
  public get isActive(): boolean {
    return this.active;
  }
  
}
