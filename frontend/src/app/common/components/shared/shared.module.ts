import { CommonModule } from '@angular/common';
import { FocusMeDirective } from '../../other/directives/focusMe.directive';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { TableIntoComponent } from './table-into-component/table-into';
import { TableComponentComponent } from './table-component/table-component.component';


@NgModule({
  declarations: [
   TableComponentComponent,
   TableIntoComponent,
   FocusMeDirective
  ],
  exports: [
    TableComponentComponent,
    TableIntoComponent,
    FocusMeDirective
  ],
  imports: [
    CommonModule,
    FontAwesomeModule
  ]
})


export class SharedModule {}
