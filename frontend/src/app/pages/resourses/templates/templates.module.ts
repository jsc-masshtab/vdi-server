import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../../shared/shared.module';
import { TemplatesComponent } from './all-templates/templates.component';
import { TemplatesService } from './all-templates/templates.service';
import { TemplateDetailsComponent } from './template-details/template-details.component';



@NgModule({
  declarations: [
    TemplatesComponent,
    TemplateDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule
  ],
  providers: [TemplatesService],
  exports: [
    TemplatesComponent,
    TemplateDetailsComponent
  ]
})
export class TemplatesModule { }
