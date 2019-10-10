import { MatDialogModule } from '@angular/material/dialog';
import { StatusPipe, StatusIconPipe } from './../../other/directives/statusEntity.directive';
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
   FormForEditComponent,
   StatusIconPipe
  ],
  exports: [
    TableComponentComponent,
    TableIntoComponent,
    FocusMeDirective,
    StatusPipe,
    FormForEditComponent,
    StatusIconPipe
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
