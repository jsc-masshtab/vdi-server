import { AddSelectComponent } from './components/shared/add-select/add-select';
import { AppRoutingModule } from '../../app-routing.module';


import { MatDialogModule } from '@angular/material/dialog';
import { StatusPipe, StatusIconPipe } from './pipes/statusEntity.pipes';
import { AssignmentTypePipe } from './pipes/assignmentType.pipes';
import { CommonModule } from '@angular/common';
import { FocusMeDirective } from './directives/focusMe.directive';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { TableIntoComponent } from './components/shared/table-into-component/table-into';
import { TableComponentComponent } from './components/shared/table-component/table-component.component';
import { FormForEditComponent } from './forms-dinamic/change-form/form-edit.component';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSelectModule } from '@angular/material/select';
import { PaginationComponent } from './components/shared/pagination/pagination.component';
import { FooterService } from './components/single/footer/footer.service';
import { YesNoFormComponent } from './forms-dinamic/yes-no-form/yes-no-form.component';
import { TranslatePipe } from './pipes/translate.pipe';


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
  StatusIconPipe,
  AssignmentTypePipe,
  TranslatePipe
];

const FORMS_DINAMIC = [
  FormForEditComponent,
  YesNoFormComponent
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
  providers: [
    FooterService
  ]
})


export class SharedModule {

  constructor() {}



}
