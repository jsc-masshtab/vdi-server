import { AddSelectComponent } from './components/shared/add-select/add-select';
import { AppRoutingModule } from '../../app-routing.module';


import { MatDialogModule } from '@angular/material/dialog';
import { StatusPipe, StatusIconPipe } from './pipes/statusEntity.pipes';
import { CommonModule } from '@angular/common';
import { FocusMeDirective } from './directives/focusMe.directive';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { TableIntoComponent } from './components/shared/table-into-component/table-into';
import { TableComponentComponent } from './components/shared/table-component/table-component.component';
import { FormForEditComponent } from './forms-dinamic/change-form/form-edit.component';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatCheckboxModule, MatSelectModule } from '@angular/material';
import { PaginationComponent } from './components/shared/pagination/pagination.component';


const COMPONENTS = [
  TableComponentComponent,
  TableIntoComponent,
  PaginationComponent,
  AddSelectComponent
];

const DIRECTIVES = [
  FocusMeDirective
];

const PIPES = [
  StatusPipe,
  StatusIconPipe
];

const FORMS_DINAMIC = [
  FormForEditComponent
];


@NgModule({
  declarations: [
    ...DIRECTIVES,
    ...PIPES,
    ...FORMS_DINAMIC,
    ...COMPONENTS
  ],
  exports: [
    ...DIRECTIVES,
    ...COMPONENTS,
    ...PIPES,
    ...FORMS_DINAMIC
  ],
  imports: [
    CommonModule,
    FontAwesomeModule,
    MatDialogModule,
    ReactiveFormsModule,
    MatCheckboxModule,
    MatSelectModule,
    AppRoutingModule,
    FormsModule
  ],
  entryComponents: [
    ...FORMS_DINAMIC
  ]
})


export class SharedModule {

  constructor() {}



}
