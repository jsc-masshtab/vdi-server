import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ControllersComponent } from './controllers.component';

describe('TemplatesComponent', () => {
  let component: ControllersComponent;
  let fixture: ComponentFixture<ControllersComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ControllersComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ControllersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
