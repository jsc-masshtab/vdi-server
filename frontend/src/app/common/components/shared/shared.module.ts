import { StatusPipe } from './../../other/directives/statusEntity.directive';
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
   FocusMeDirective,
   StatusPipe
  ],
  exports: [
    TableComponentComponent,
    TableIntoComponent,
    FocusMeDirective,
    StatusPipe
  ],
  imports: [
    CommonModule,
    FontAwesomeModule
  ]
})


export class SharedModule {}
