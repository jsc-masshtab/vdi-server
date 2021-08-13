import { AfterContentInit, Component, ContentChildren, QueryList } from '@angular/core';
import { TabComponent } from './tab/tab.component';

@Component({
  selector: 'vdi-tabs',
  templateUrl: './tabs.component.html',
  styleUrls: ['./tabs.component.scss']
})
export class TabsComponent implements AfterContentInit {
  @ContentChildren(TabComponent) tabs: QueryList<TabComponent>;

  public ngAfterContentInit(): void{
    let activeTabs = this.tabs.filter( (tab) => tab.active);
    
    if (activeTabs.length === 0) {
      this.selectTab(this.tabs.first);
    }
  }
  
  public selectTab(tab: TabComponent): void{
    this.tabs.toArray().forEach( (t: TabComponent) => t.active = false);
    
    tab.active = true;
  }
  
}
