import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { TemplateDetailsComponent } from './template-details.component';
import { TemplatesService } from '../all-templates/templates.service';

describe('TemplateDetailsComponent', () => {
  let component: TemplateDetailsComponent;
  let fixture: ComponentFixture<TemplateDetailsComponent>;

  let serviceStub: Partial<TemplatesService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getTemplate(): any {
        return {
          valueChanges: of({
            data: {
              template: []
            }
          })
        };
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ TemplateDetailsComponent ],
      providers: [
        {
          provide: TemplatesService,
          useValue: serviceStub
        },
        {
          provide: MatDialog,
          useValue: {}
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TemplateDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
