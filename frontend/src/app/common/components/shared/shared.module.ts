import { MatDialogModule } from '@angular/material/dialog';
import { StatusPipe } from './../../other/directives/statusEntity.directive';
import { CommonModule } from '@angular/common';
import { FocusMeDirective } from '../../other/directives/focusMe.directive';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { TableIntoComponent } from './table-into-component/table-into';
import { TableComponentComponent } from './table-component/table-component.component';
import { FormForEditComponent } from './change-form/form-edit.component';
import { FormsModule } from '@angular/forms';


@NgModule({
  declarations: [
   TableComponentComponent,
   TableIntoComponent,
   FocusMeDirective,
   StatusPipe,
   FormForEditComponent
  ],
  exports: [
    TableComponentComponent,
    TableIntoComponent,
    FocusMeDirective,
    StatusPipe,
    FormForEditComponent
  ],
  imports: [
    CommonModule,
    FontAwesomeModule,
    MatDialogModule,
    FormsModule
  ],
  entryComponents: [
    FormForEditComponent
  ]
})


export class SharedModule {}
